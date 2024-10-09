# JETAA UK Event Notifier Slackbot

## Overview

The JETAA UK Event Notifier Slackbot is a Python-based service designed to assist the Japan Exchange and Teaching Programme Alumni Association United Kingdom (JETAA UK) in discovering and sharing Japan-related events in London. It automates event discovery by scanning designated websites and posting new events directly into a specified Slack channel, helping members stay informed about a range of activities, including cultural events, social gatherings, and professional opportunities.

## Problem Statement

Committee members of JETAA UK sought a more efficient way to find and share information about Japan-related events in London. Manually monitoring multiple websites was time-consuming and often resulted in missed opportunities. The solution was to create an automated service that posts events directly to a Slack channel, ensuring timely and consistent event notifications for the entire community.

## Justification for Web Scraping

Web scraping is not considered a best practice when official APIs are available, as it can place additional load on websites and may be subject to changes in the site's structure. However, in this case, the decision to use scraping was justified because:

- **No Available APIs**: The targeted websites did not offer public APIs for accessing event information, making scraping the only viable solution for automatically gathering event data.
- **Consistent Data Access**: Scraping allows the service to keep data up-to-date and ensures that JETAA UK members receive timely notifications about new events.
- **Respectful Scraping Practices**: The service was designed to be respectful of the source websites by scraping infrequently (e.g., daily) and only accessing relevant pages. Proper error handling and logging ensure minimal disruption if the structure of the websites changes.

## Scope

The application includes the following features:

- Automated event scraping from multiple sources, including:
  - [JETAA UK Calendar](https://www.jetaa.org.uk/events/events-calendar/)
  - [Japan House London](https://www.japanhouselondon.uk/whats-on/)
  - [Japan Society](https://www.japansociety.org.uk/events?eventcat=0&eventpage=0)
  - [Japan Foundation](https://www.jpf.org.uk/whatson.php)
- Posting event details to a specified Slack channel for real-time notifications.
- Handling duplicate events by comparing previously posted data.
- Logging event data for auditing and troubleshooting purposes.

## Services and Technologies Used

The application leverages several AWS services and libraries, chosen with cost-effectiveness in mind. The selected services were chosen because their free tiers more than met the application's requirements, allowing the project to be developed and maintained without incurring significant costs. The services used include:

- **AWS Lambda** for serverless execution
- **AWS S3** for storage of logs and temporary files
- **AWS SES (Simple Email Service)** for sending alerts or notifications outside Slack
- **Slack API** for integration with Slack to post events
- **Python Libraries** such as `requests`, `BeautifulSoup` for web scraping, and `boto3` for AWS integration

## Maintenance Considerations

- **Website Changes**:  
  If the structure of any target website changes, the scraping logic in the respective scraper files may need to be updated.
- **AWS Costs**:  
  Regularly monitor usage in the AWS console to ensure the service remains within free tier limits.
- **Slack Channel Configuration**:  
  Ensure that the Slack channel ID and token are kept secure. Rotate the tokens periodically for security.

## Running the JETAA UK Event Notifier Slackbot Locally

Follow these steps to clone the repository, configure the environment, and run the JETAA UK Event Notifier Slackbot locally on your machine.

### Prerequisites

Make sure you have the following installed:

- **Python 3.8+**
- **Git**

### Step 1: Clone the Repository

First, clone the repository from GitHub:

```bash
git clone https://github.com/yourusername/jetaa-event-notifier-slackbot.git
```

Navigate into the project directory:

```bash
cd jetaa-event-notifier-slackbot
```

### Step 2: Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install the Required Dependencies

Install the necessary Python libraries using `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

You'll need to configure environment variables for AWS credentials and Slack tokens. You can create a `.env` file in the project root directory to manage these.

Create a `.env` file:

```bash
touch .env
```

Add the following environment variables to the `.env` file:

```
SLACK_API_TOKEN=your_slack_api_token
SLACK_CHANNEL_ID=your_slack_channel_id
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION_NAME=your_aws_region
```

Replace the placeholder values with your actual credentials.

### Step 5: Run the Application Locally

To test the Slackbot locally, you can run the main script that initiates the event scraping and posting process. For example:

```bash
python main.py
```

This will scrape the configured event sources and attempt to post the results to the specified Slack channel.

### Step 6: Troubleshooting

- **Scraping Issues**: If the scrapers fail, check the structure of the target websites and adjust the scraping logic as needed.
- **Environment Variables Not Loaded**: Make sure you are in the correct directory and that the `.env` file is properly configured.

### Step 7: Optional: Running Unit Tests

You can run the provided unit tests to ensure everything is working as expected:

```bash
pytest
```

### Step 8: Deactivate the Virtual Environment (Optional)

After you finish running the application, you can deactivate the virtual environment:

```bash
deactivate
```

## Packaging and Deploying the JETAA UK Event Notifier Slackbot to AWS Lambda

Follow these steps to package the application into a zip file and deploy it to AWS Lambda:

### Prerequisites

Make sure you have the following installed:

- **Python 3.8+**
- **AWS CLI** (configured with your AWS credentials)

### Step 1: Prepare the Project for Deployment

1. **Generate the `requirements.txt` file**  
   This ensures that all the necessary dependencies are included:

   ```bash
   pip freeze > requirements.txt
   ```

2. **Install the dependencies into a separate directory (`package`)**  
   This step is needed to include the dependencies in the Lambda deployment package:
   ```bash
   pip install -r requirements.txt --target ./package
   ```

### Step 2: Create the Deployment Package

1. **Zip the entire project folder**  
   Use the following command to create a zip file named `function.zip`, excluding certain folders like `__pycache__`, `venv`, and `.git`:

   ```bash
   zip -r function.zip . -x "__pycache__/*" "venv/*" ".git/*"
   ```

2. **Navigate to the `package` directory**  
   Move into the `package` folder where the dependencies were installed:

   ```bash
   cd package
   ```

3. **Add the dependencies to the `function.zip` file**  
   This step ensures that all required libraries are included in the deployment package:

   ```bash
   zip -r ../function.zip .
   ```

4. **Go back to the main project directory**

   ```bash
   cd ..
   ```

5. **Add the main Python files and other resources**  
   Include your script files and any additional assets such as logos:
   ```bash
   zip -g function.zip *.py event_source_logos/*
   ```

### Step 3: Deploy the Package to AWS Lambda

1. **Update the Lambda function code**  
   Make sure the Lambda function name matches the one you're updating:
   ```bash
   aws lambda update-function-code --function-name JETAAEventNotifier --zip-file fileb://function.zip
   ```

### Step 4: Configure the Lambda Function

- **Set up environment variables**:  
  Make sure to configure any necessary environment variables, such as Slack tokens and AWS credentials, within the Lambda function settings.

- **Set up a trigger using CloudWatch Events**:  
  Configure a CloudWatch Events rule to trigger the Lambda function on a schedule (e.g., once a day).

### Notes

- **Excluding Folders**: The `-x "__pycache__/*" "venv/*" ".git/*"` option in the zip command excludes unwanted folders to keep the package size minimal.
- **Dependencies Handling**: Using a separate `package` directory ensures that all necessary Python libraries are included in the Lambda deployment.
