# Mailchimp merge

Usage:

```bash
pip install -r requirements.txt  # Install requirements
export MAILCHIMP_KEY="..."       # Your mailchimp api key
export MAILCHIMP_DATACENTER=us7  # Your mailchimp datacenter id
python main.py > output.csv      # output.csv contains your merged list
```

Outputs a tab-delimited list of the form:

|Email Address   |First Name|Last Name|Phone Number |Original list ID|
|----------------|----------|---------|------------ |----------------|
|test@example.com|James     |Brown    |+1 1235556789|abcdefg         |

...etc.