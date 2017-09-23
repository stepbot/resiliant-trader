from pymongo import MongoClient
import datetime
import random

try:
    import config
    print('using local config file')
    mongodb_uri = config.mongodb_uri
except:
    print('using environment variable')
    mongodb_uri = os.getenv('MONGODB_URI')

print("Generating Test Data")
success = True
now = datetime.datetime.utcnow()
year = datetime.timedelta(days=365)
minute = datetime.timedelta(minutes=1)
start = now-year
fakeNow = start

if success:
    try:
        client = MongoClient(mongodb_uri)
        db = client.get_database()
    except Exception as e:
        print('mongo login error ', str(e))
        success = False

while fakeNow < now:
    if fakeNow.isoweekday() in range(1, 6):
        if fakeNow.hour*60+fakeNow.minute in range(13*60+30, 20*60):
            # gonna act like this is a minute where the market was open but maybe not because daylight savings and holidays, but shouldnt matter for testing anyway
            spyChange = ((1+(random.normalvariate(0.0002939, 0.0097392)))**(1/390))-1
            tltChange = ((1+(random.normalvariate(0.0002939, 0.0097392)))**(1/390))-1
            assignmentWeight = random.uniform(0.0,1.0)

            if success:
                try:
                    # save data
                    percentageData = {
                        "timestamp":fakeNow,
                        "spy":spyChange,
                        "tlt":tltChange,
                        "portfolio":assignmentWeight*spyChange+(1-assignmentWeight)*tltChange,
                        "90dayTreasury":0.00000010426
                    }
                    data_id = db.percentageMoveTest.insert_one(percentageData).inserted_id
                except Exception as e:
                    print('data save error ', str(e))
                    success = False
    fakeNow+=minute
