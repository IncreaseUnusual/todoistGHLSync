import csv
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# API endpoint and authorization token

location_id = 'YOUR LOCATION ID'

api_url = f'https://services.leadconnectorhq.com/locations/{location_id}/tasks/search'

webhook_url = "YOUR WEBHOOK URL HERE"

token = ""

todoist_token = 'YOUR TODOIST TOKEN'

todoist_url = 'https://api.todoist.com/rest/v2/tasks'

csv_file_path = 'tasks.csv'

assigned_to =  ["CONTACT ID"]


def load_existing_tasks_from_csv():
    existing_tasks = {}
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_tasks[row['id']] = row
    except FileNotFoundError:
        pass
    return existing_tasks

def add_task_to_csv(task):
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'title', 'body', 'assignedTo', 'dueDate', 'contactId'], quoting=csv.QUOTE_ALL)
        body = task.get('body', '').replace('\n', '\\n')
        writer.writerow({
            'id': task.get('id', ''),
            'title': task.get('title', ''),
            'body': body,
            'assignedTo': task.get('assignedTo', 'null'),
            'dueDate': task.get('dueDate', ''),
            'contactId': task.get('contactId', 'null')
        })

def add_tasks_to_todoist(tasks):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {todoist_token}',
    }
    
    for task in tasks:
        date = task.get('dueDate', 'null').split('T')[0]
        task_data = {
            'content': task.get('title', ''),
            'description': task.get('body', '') + f"\n id: {task.get('id', '')}",
            'project_id': 'PROJECT ID HERE',
            'due_date': date,
            #INSERT LABEL AND Project Id
            'labels': ['YOUR LABEL HERE']
        }
        response = requests.post(todoist_url, headers=headers, json=task_data)
        if response.status_code == 200:
            print(f"Task '{task_data['content']}' added successfully.")
        else:
            print(f"Error adding task '{task_data['content']}': {response.status_code}, {response.text}")

def fetch_data_from_webhook(url, timeout=10):
    """
    Fetch data from the webhook URL.

    Returns:
    - str: The fetched token as a string.
    """
    try:
        webhook_response = requests.get(webhook_url, timeout=timeout)
        webhook_response.raise_for_status()  # Raise an HTTPError if the response was an error
        # Extract token from the response (assuming the token is in the response body)
        data = webhook_response.text.split("Bearer")[1].strip()
        return data
    except requests.exceptions.Timeout:
        print(f"Error: Request timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from webhook: {e}")
    except IndexError as ie:
        print(f"Error parsing token from response: {ie}")
    return ""

# Function to fetch tasks from the API and filter out completed tasks
def fetch_and_filter_tasks():
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Version': '2021-07-28'
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        tasks = response.json().get('tasks', [])
        # Filter out completed tasks
        incomplete_tasks = [task for task in tasks if not task.get('completed')]
        return incomplete_tasks
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []
    

def main():
    global token
    token = fetch_data_from_webhook(webhook_url)
    existing_tasks = load_existing_tasks_from_csv()

    incomplete_tasks = fetch_and_filter_tasks()

    # Filter tasks to match the assigned_to value
    filtered_tasks = [task for task in incomplete_tasks if task.get('assignedTo') == assigned_to]

    new_tasks = [task for task in filtered_tasks if task['id'] not in existing_tasks]

    if new_tasks:
        add_tasks_to_todoist(new_tasks)

        for task in new_tasks:
            add_task_to_csv(task)

    if not new_tasks:
        print("No new tasks to add.")
    else:
        print("New tasks processed.")


if __name__ == "__main__":
    main()
