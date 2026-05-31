from locust import HttpUser, task, between

class BlogUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def feed(self):
        self.client.get('/blog/?limit=10')

    @task(1)
    def trending(self):
        self.client.get('/blog/trending/tags')

    @task(1)
    def search(self):
        self.client.get('/blog/?search=fastapi&limit=5')
