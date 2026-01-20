from utils import match


def test_supplies_post(sess, client):
    sess.commit()

    json = {"start_date": "2024-05-01T00:00:00Z", "finish_date": "2024-05-01T00:00:00Z"}
    response = client.post("/api/v1/supplies", json=json)
    match(response, 200)
