
class GlobalTestState:
    __instance = None
    @staticmethod
    def getInstance():
      """ Static access method. """
      if GlobalTestState.__instance == None:
         GlobalTestState()
      return GlobalTestState.__instance


    def __init__(self):
        """ Virtually private constructor. """
        self.test_run_mode = False
        self.test_capture_mode = False
        self.test_id = ''
        self.session_id = 0
        if GlobalTestState.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            GlobalTestState.__instance = self

    def set_test_run_mode(self, test_run_mode):
        self.test_run_mode = test_run_mode

    def get_test_run_mode(self):
        return self.test_run_mode
    
    def set_test_capture_mode(self, test_capture_mode):
        self.test_capture_mode = test_capture_mode

    def get_test_capture_mode(self):
        return self.test_capture_mode
    
    def set_test_id(self, test_id):
        self.test_id = test_id

    def get_test_id(self):
        return self.test_id
    
    def set_session_id(self, session_id):
        self.session_id = session_id

    def get_session_id(self):
        return self.session_id
    

# Create the singleton here
GlobalTestState()
