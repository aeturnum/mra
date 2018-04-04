class Settings(object):
    pass

class Plan(object):
    PATH = "Plan"
    def __init__(self, *tasks):
        self.tasks = list(tasks)

    def run(self):
    # setup queue
        queue = []
        for task in self.tasks:
            queue.append(task)

        while True:
            if not queue:
                break

            task = queue.pop(0)
            print(f"{task}")
            if not task.ready():
                print(f"Task is not ready! Returning to queu")
                queue.append(task)

            task.advance()
            if not task.done:
                queue.append(task)

