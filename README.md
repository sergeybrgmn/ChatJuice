# ChatJuice will squeeze the essence

## About the solution

The solution should help to catch up on the discussions from your group chats. 

Do you remember the last time your had 200-300-1000-3000 unread messages in a community chat. An absolutely no time to engage last week and no energy to read 'em all. 

Much easier when all the missed messages are segmented into threads and you know what was the topic name of this thread. 
After that it's up to you to decide if you are interestred to read this thread. 

That's exactly what ChatJuice does, just "squeeze the essence" of the thread and "says" (hello GenAI) it in a few words. 

## ChatJuice bot

* Currently working with Telegram only.
* The [TG bot](bot.py) is used as an interface, taking user commands and showing the results (bot.py)
* The [access to user messages](connect.py) is implemented with Telethon lib.
* OpenAI API is used to summarize the topic name (hello $0.02/1K tokens in Davinci model)
* The [thread grouping](topic_sense.py) is organized based in heuristic approach 
* All the user, requests and balance [data is managed](dataflow.py) with SQLite lib. The low-level queries are defined [here](db.py)


## Main userflow

Topics in the missed discussions:
1) Login to your TG account  
2) **/miss** command to get the list of the chats with unread messages (DESC order)
3) select the chat to "squeeze the juice"
4) Get the list of topics discussed with links to the start of the topic discussion

## Privacy issue

ChatJuice is not storing the original messages in the database, only the result of summarization with no connection to any person.

## Project Roadmap
### WIP
* Show number of topics detected
* Improve grouping into threads


### High Confidence, Big Impact features, Easy (ICE):
* Calculate the token consumption for each user
* Predict cost of the summary request before use

### High Confidence, Big Impact features, not easy (ICe):
* Offer free summarization bazed on the requests of others - helps to attract new users for free.

### low confidence, Big impact features, not easy (Ice)
This things need a research.
* Detect and record recommendation 
* NN to detect new topic


### low confidence, small impact features, not easy (ice)



