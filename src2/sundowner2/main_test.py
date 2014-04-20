import httplib
import json
import pymongo
import requests
import unittest


HOST_API = "http://localhost:8888"
HOST_DB = "ubuntu"
USER_A = "James"
USER_B = "Annie"

class FooTest(unittest.TestCase):

    def setUp(self):
        self.db = pymongo.MongoClient(HOST_DB).minitag
        self.db.tags.remove()


    # Normal -------------------------------------------------------------------

    def test_get_no_tags(self):
        params = {
            "user_id":  USER_A,
            "lat":      1,
            "lng":      1,
            }
        r = requests.get(HOST_API+"/tags/", params=params)
        assert r.json()["data"] == []

    def test_get_match(self):

        # create a post by USER_A
        data = json.dumps({
            "lat":      1,
            "lng":      1,
            "text":     "hello",
            "user_id":  USER_A,
            })
        r = requests.post(HOST_API+"/tags/", data=data)
        tag_id = r.json()["data"]["tag_id"]

        # if USER_A requests tags there should be none as users don't see their
        # own tags
        params = {
            "user_id":  USER_A,
            "lat":      1,
            "lng":      1,
            }
        r = requests.get(HOST_API+"/tags/", params=params)
        assert r.json()["data"] == []

        # if USER_B requests tags they should see the tag created by USER_A
        params = {
            "user_id":  USER_B,
            "lat":      1,
            "lng":      1,
            }
        r = requests.get(HOST_API+"/tags/", params=params)
        assert r.json()["data"] == [{
            "id":       tag_id,
            "lat":      1,
            "lng":      1,
            "user_id":  USER_A,
            "text":     "hello",
            }]

    def test_post_first_tag(self):
        data = json.dumps({
            "lat":      1,
            "lng":      1,
            "text":     "hello",
            "user_id":  USER_A,
            })
        r = requests.post(HOST_API+"/tags/", data=data)
        assert "tag_id" in r.json()["data"]
        assert self.db.tags.count() == 1

    def test_delete(self):

        # create a post by USER_A
        data = json.dumps({
            "lat":      1,
            "lng":      1,
            "text":     "hello",
            "user_id":  USER_A,
            })
        r = requests.post(HOST_API+"/tags/", data=data)
        tag_id = r.json()["data"]["tag_id"]

        # if USER_B requests tags they should see the tag
        params = {
            "user_id":  USER_B,
            "lat":      1,
            "lng":      1,
            }
        r = requests.get(HOST_API+"/tags/", params=params)
        assert len(r.json()["data"]) == 1

        # delete the post
        params = {
            "user_id":  USER_B,
            }
        r = requests.delete(HOST_API+"/tags/"+tag_id, params=params)
        assert r.json()["meta"]["code"] == httplib.OK
        assert "data" not in r.json()

        # if USER_B requests tag they shouldn't see any now
        params = {
            "user_id":  USER_B,
            "lat":      1,
            "lng":      1,
            }
        r = requests.get(HOST_API+"/tags/", params=params)
        assert len(r.json()["data"]) == 0


    # Bad Request --------------------------------------------------------------

    def test_delete_tag_youre_not_a_recipient_of(self):

        # create a post by USER_A
        data = json.dumps({
            "lat":      1,
            "lng":      1,
            "text":     "hello",
            "user_id":  USER_A,
            })
        r = requests.post(HOST_API+"/tags/", data=data)
        tag_id = r.json()["data"]["tag_id"]

        # USER_A shouldn't be able to delete the tag because they aren't a
        # recipient
        params = {
            "user_id":  USER_A,
            }
        r = requests.delete(HOST_API+"/tags/"+tag_id, params=params)
        print r.json()

if __name__ == "__main__":
    unittest.main()

