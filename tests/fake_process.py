class FakeProcess:
    def __init__(self, input_cmd):
        self.input_cmd = input_cmd

    def communicate(self, command_input):
        # You can inspect the command_input to customize behaviour,
        # For example, if command_input equals "module spider v1"
        # simulate the shell output after sourcing mock.sh
        if "module spider python/v1" in command_input:
            # The output is simulated based on how your mock.sh behaves.
            # In this case, we expect find_python_modules to iterate over:
            #   <some output line>
            #   "You will need to load all module(s)"
            #   then two lines corresponding to modules.
            fake_output = """\
            You will need to load all module(s)
            
            Module1
            Module2
            """
            return (fake_output, "")

        if "module spider python" in command_input:
            fake_output = "python/\npython/v1"
            return (fake_output, "")

        if "module load" in command_input:
            fake_output = "modules loaded"
            return (fake_output, "")

        if "virtualenv" in command_input:
            fake_output = "virtualenv created"
            return (fake_output, "")

        if "source" in command_input:
            fake_output = "source created"
            return (fake_output, "")

        if "pip install" in command_input:
            fake_output = "pip installed"
            return (fake_output, "")

        raise ValueError(command_input)
