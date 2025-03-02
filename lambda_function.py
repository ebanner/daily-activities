import os

import json

import boto3

from datetime import datetime, timedelta

s3_client = boto3.client('s3')

def put(key, value, bucket='storage9'):
    value_json = json.dumps(value)
    print('value_json', value_json, type(value_json))
    s3_client.put_object(Bucket=bucket, Key=key, Body=value_json)

def get(key, bucket='storage9'):
    try:
        object = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        print(e)
        return None

    value_json = object['Body'].read().decode('utf-8')
    value = json.loads(value_json)
    return value

def get_day_key():
    date_time_utc = datetime.now()
    date_time_est = date_time_utc - timedelta(hours=5)
    day_str = date_time_est.strftime("%Y%m%d")
    return day_str

def get_html(ACTIVITIES):
    html = """

    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js"></script>
      <style>
      * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          font-family: Arial, sans-serif;
      }
      </style>
    </head>
    <body style="margin: 0">
      <div id="swipe-element" style="width: 100vw; height: 100vh; background: lightblue; text-align: center;">
          <h1 style="padding-top: 25vh; font-size: 128px;">Swipe me to get a random activity!</h1>
      </div>
      
      <script>
        document.body.addEventListener("touchmove", function(event) {
          event.preventDefault(); // Stops scrolling
        }, { passive: false });

        const element = document.getElementById('swipe-element');
        const hammer = new Hammer(element);

        let i = 0;

        let activities = <<MY_ACTIVITIES>>;

        function shuffleArray(arr) {
          for (let i = arr.length - 1; i > 0; i--) {
            let j = Math.floor(Math.random() * (i + 1)); // Random index from 0 to i
            [arr[i], arr[j]] = [arr[j], arr[i]]; // Swap elements
          }
          return arr;
        }

        shuffleArray(activities);

        function getRandomElement(arr) {
          return arr[Math.floor(Math.random() * arr.length)];
        }

        function setH1(text) {
          document.querySelector("h1").textContent = text;
        }

        function goLeft() {
          i -= 1;
          if (i == -1)
            i = activities.length - 1;
          return activities[i];
        }

        function goRight() {
          i += 1;
          i %= activities.length;
          return activities[i];
        }

        function deleteElement() {
          activities.splice(i, 1);
          if (i == activities.length)
            i -= 1
          return activities[i];
        }

        function markCompleted() {
          const activity = activities[i];
          fetch("/mark_completed", {
              method: 'POST',
              body: JSON.stringify({
                  'activity': activity
              })
          });
          activities.splice(i, 1);
          if (i == activities.length)
            i -= 1;
          return activities[i];
        }

        function reset() {
          fetch("/reset", { method: 'POST' });
          activities = ["Cardio", "Strength training", "LeetCode", "Good thing"];
          i = 0;
          return activities[0];
        }
        
        hammer.on('swipeleft', () => setH1(goRight()));
        hammer.on('swiperight', () => setH1(goLeft()));
        hammer.on("tap", () => setH1(markCompleted()));
        hammer.on("swipedown", () => alert("Down!"));
        hammer.on("press", () => setH1(reset()));

        setH1(activities[i]);
      </script>
    </body>
    </html>

    """.replace('<<MY_ACTIVITIES>>', str(ACTIVITIES))

    print(html.replace('\n', ''))

    return html

def get_body(event):
    body = json.loads(event['body'])
    return body

def lambda_handler(event, context):
    DAY_KEY = get_day_key()
    ACTIVITIES = get(DAY_KEY)
    if ACTIVITIES == None:
        ACTIVITIES = ["Cardio", "Strength training", "LeetCode", "Good thing"]
        put(DAY_KEY, ACTIVITIES)

    print('fetched ACTIVITIES', ACTIVITIES)
    
    if event.get('rawPath') == '/mark_completed':
        body = get_body(event)
        activity = body['activity']
        ACTIVITIES.remove(activity)
        put(DAY_KEY, ACTIVITIES)
        activities = get(DAY_KEY)
        return {
            "statusCode": 200,
            "body": activity,
        }
    elif event.get('rawPath') == '/reset':
        ACTIVITIES = ["Cardio", "Strength training", "LeetCode", "Good thing"]
        put(DAY_KEY, ACTIVITIES)
        return {
            "statusCode": 200,
            "body": "Reset",
        }
    else:
        html = get_html(ACTIVITIES)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html",
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            },
            "body": html
        }

