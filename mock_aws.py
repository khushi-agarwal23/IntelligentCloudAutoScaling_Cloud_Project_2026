class MockAutoScalingGroup:

    def __init__(self, initial_instances=1, min_instances=1, max_instances=3):
        self.instances = initial_instances
        self.min_instances = min_instances
        self.max_instances = max_instances

    def scale_in(self):
        if self.instances > self.min_instances:
            self.instances -= 1
            return f"Scaled in to {self.instances} instances"

        return f"Already at minimum capacity: {self.instances} instances"

    def maintain(self):
        return f"Maintaining {self.instances} instances"

    def scale_out(self):
        if self.instances < self.max_instances:
            self.instances += 1
            return f"Scaled out to {self.instances} instances"

        return f"Already at maximum capacity: {self.instances} instances"

    def apply_action(self, action):
        """
        Actions:
        0 = scale in
        1 = maintain
        2 = scale out
        """

        if action == 0:
            message = self.scale_in()

        elif action == 1:
            message = self.maintain()

        elif action == 2:
            message = self.scale_out()

        else:
            raise ValueError("Invalid action. Use 0, 1, or 2.")

        return {
            "action": action,
            "instances": self.instances,
            "message": message
        }