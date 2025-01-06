import subprocess
import sys
import time
import argparse

class K6Runner:
    
    def __init__(self, target_vus, duration, rampup_time, test_script, verbose):
        self.target_vus = target_vus
        self.duration = duration
        self.rampup_time = rampup_time
        self.test_script = test_script
        self.verbose = verbose


    def run(self):
        print(f"Running K6 with {self.target_vus} VUs for {self.duration}s (ramp-up: {self.rampup_time}s)...")
        cmd = [
            "k6", "run",
            "-e", f"VUS={self.target_vus}",
            "-e", f"RAMPUP={self.rampup_time}s",
            "-e", f"DURATION={self.duration}s",
            self.test_script
        ]
        return self.k6_logging_catcher(cmd)
        
        
    def k6_logging_catcher(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if stdout:
            error_lines = [line for line in stderr.split("\n") if "level=error" in line and "msg=\"threshold" not in line]
            check_lines = [line for line in stdout.split("\n") if "http_req_failed" in line]
            if error_lines:
                print(f"\nK6 script encountered errors:\n{error_lines[len(error_lines)-2]}")
                sys.exit(f"\nProblem with the K6 script. Exiting...")
            if check_lines:
                print(f"failed requests: {check_lines[0].split(':', 1)[1].strip()}")
        if self.verbose:
            print(stdout)
            if stderr:
                print(f"Error: {stderr}")
        process.wait()
        return process.returncode == 0


class VUTester:
    def __init__(self, initial_vus, increment, validation_runs, delay_between_tests, duration, rampup_time, fails_allowed, test_script, verbose):
        self.initial_vus = initial_vus
        self.increment = increment
        self.validation_runs = validation_runs
        self.delay_between_tests = delay_between_tests
        self.duration = duration
        self.rampup_time = rampup_time
        self.fails_allowed = fails_allowed
        self.test_script = test_script
        self.verbose = verbose
        self.test_count = 1

    def find_max_vus_increasing(self):
        current_vus = self.initial_vus
        failed_tests = 0
        while True:
            print(f"Test #{self.test_count}")
            self.test_count += 1
            if failed_tests > 0:
                print(f"Fails: {failed_tests}/{self.fails_allowed}")
            runner = K6Runner(current_vus, self.duration, self.rampup_time, self.test_script, self.verbose)
            passed = runner.run()
            if passed:
                failed_tests = 0
                print(f"\033[92;1;4mTest passed for {current_vus} VUs.\033[0m")
                current_vus += self.increment
                print(f"Waiting {self.delay_between_tests} seconds before the next test...\n")
                time.sleep(self.delay_between_tests)
            else:
                print(f"\033[31;1;4mTest failed for {current_vus} VUs.\033[0m")
                if failed_tests == self.fails_allowed:
                    reduced_vus = current_vus - (self.increment // 2)
                    print(f"Reducing VUs to {reduced_vus}. Now validating...\n")
                    time.sleep(self.delay_between_tests)
                    return self.find_max_vus_decreasing(reduced_vus)
                failed_tests += 1
                print(f"Waiting {self.delay_between_tests} seconds before the next test...\n")
                time.sleep(self.delay_between_tests)

    def find_max_vus_decreasing(self, reduced_vus):
        while True:
            if reduced_vus <= 0:
                print("The VU count has reached zero. The testing process failed. Exiting...")
                return 0
            if self.validate_max_vus(reduced_vus):
                return reduced_vus
            else:
                print(f"\033[31;1;4mValidation failed for {reduced_vus} VUs.\033[0m")
                reduced_vus -= (self.increment // 2)
                print(f"Reducing VUs further to {reduced_vus} and validating again...\n")

    def validate_max_vus(self, max_vus):
       print(f"\033[93m\nValidating maximum VU count: {max_vus}")
       print("---------------------------\n\033[0m")
       failed_tests = 0
       i = 0
    
       while i < self.validation_runs:
          print(f"Test #{self.test_count}")
          self.test_count += 1
          print(f"Validation run {i+1}/{self.validation_runs}")
        
          if failed_tests > 0:
            print(f"Fails: {failed_tests}/{self.fails_allowed}")
        
          runner = K6Runner(max_vus, self.duration, self.rampup_time, self.test_script, self.verbose)
          passed = runner.run()
           
          if not passed:
            print(f"\033[31;1;4mValidation run {i+1} failed.\033[0m")
            if failed_tests >= self.fails_allowed:
                return False
            failed_tests += 1
            i -= 1
            print(f"Retrying run {i+2}")
          else:
            print(f"\033[92;1;4mValidation run {i+1} passed.\033[0m")
        
          if i + 1 < self.validation_runs:
            print(f"Waiting {self.delay_between_tests} seconds before the next validation test...\n")
            time.sleep(self.delay_between_tests)
        
          i += 1
        
       return True

def validate_positive_int(value, name):
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise ValueError(f"{name} must be a positive integer.")
        if ivalue > 10000000:
            raise ValueError(f"{name} must not exceed 10000000.")
        return ivalue
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

def validate_positive_or_zero_int(value, name):
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise ValueError(f"{name} must be a positive integer.")
        if ivalue > 10000000:
            raise ValueError(f"{name} must not exceed 10000000.")
        return ivalue
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

def banner():
    print("\033[H\033[J", end="")
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RESET = "\033[0m"
    print("Automated K6 VU testing")
    print(f""" 
   {GREEN} $$\\       $$$$$$$$\\          {ORANGE} /^\\_
   {GREEN} $$ |      \\____$$  |      o_/{ORANGE}^   \\
   {GREEN} $$ |  $$\\     $$  /       /_{ORANGE}^     `_
   {GREEN} $$ | $$  |   $$  /        \\{ORANGE}/^       \\
   {GREEN} $$$$$$  /   $$  /        {ORANGE} / ^        `\\
   {GREEN} $$  _$$<   $$  /       {ORANGE} /`            `\\
   {GREEN} \\__|  \\__|\\__/       {ORANGE}  /________________|    
   
------------------------------------------------------------------------------------{RESET}""")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Automated K6 VU testing.")
    parser.add_argument("-vu", "--initial_vus", type=lambda x: validate_positive_int(x, "Initial VUs"), help="Initial number of virtual users. Use a lower initial value when the tests fail immediately.")
    parser.add_argument("-i", "--increment", type=lambda x: validate_positive_int(x, "Increment"), help="Increment for VUs. Lower values increase the accuracy of the test. however, it will take longer to find the maximum stable VU count. Recommended: 100.")
    parser.add_argument("-vr", "--validation_runs", type=lambda x: validate_positive_or_zero_int(x, "Validation runs"), help="Number of validation runs (default: 4).")
    parser.add_argument("-d", "--delay_between_tests", type=lambda x: validate_positive_or_zero_int(x, "Delay between tests"), help="Delay between tests in seconds (default: 10).")
    parser.add_argument("-t", "--duration", type=lambda x: validate_positive_int(x, "Duration"), help="K6 test duration in seconds (default: 60).")
    parser.add_argument("-rt", "--rampup_time", type=lambda x: validate_positive_or_zero_int(x, "Rampup time"), help="Ramp-up time in seconds (default: 15).")
    parser.add_argument("-f", "--fails", type=lambda x: validate_positive_or_zero_int(x, "Fails allowed"), help="Amount of fails allowed before decreasing VU's. Probably should keep this below the amount of validation runs. (default: 1).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output. Shows K6 logs.")
    parser.add_argument("--k6_script", type=str, help="Path to the K6 test script. Please refer to the template test-script.js")
    return parser.parse_args()

def main():
    banner()
    args = parse_arguments()
    
    test_script = args.k6_script or "Scripts/test-script.js"

    while True:
        try:
            initial_vus = args.initial_vus or validate_positive_int(input("Enter the initial number of virtual users (VUs): "), "Initial VUs")
            break
        except argparse.ArgumentTypeError as e:
            print(e)
    while True:
        try:
            increment = args.increment or validate_positive_int(input("Enter the increment the VU amount increases with each test: "), "Increment")
            break
        except argparse.ArgumentTypeError as e:
            print(e)
    
    
    if not any(vars(args).values()):
        
        while True:
            try:
                validation_runs = validate_positive_or_zero_int(input("Enter the number of validation runs (recommended: 4): "), "Validation runs")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        while True:
            try:
                delay_between_tests = validate_positive_or_zero_int(input("Enter the delay between tests (in seconds): "), "Delay between tests")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        while True:
            try:
                duration = validate_positive_int(input("Enter the duration of a test (in seconds): "), "Duration")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        while True:
            try:
                rampup_time = validate_positive_or_zero_int(input("Enter the ramp up time (in seconds): "), "Ramp up time")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        while True:
            try:
                fails_allowed = validate_positive_or_zero_int(input("Enter the amount of fails alllowed: "), "amount of fails allowed before decreasing VU's")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        print("\033[93m------------------------------------------------------------------------------------\n\033[0m")
    else:
        validation_runs = args.validation_runs or 4
        delay_between_tests = args.delay_between_tests or 10
        duration = args.duration or 60
        rampup_time = args.rampup_time or 15
        fails_allowed = args.fails or 1

    print("\n\033[93mFinding the breakpoint.")
    print("---------------------------\n\033[0m")

    tester = VUTester(initial_vus, increment, validation_runs, delay_between_tests, duration, rampup_time, fails_allowed, test_script, args.verbose)
    max_vus = tester.find_max_vus_increasing()

    if max_vus > 0:
        print(f"\n\033[93m----------------------------------------------------------\nSuccessfully validated {max_vus} as the maximum stable VU count.\n----------------------------------------------------------\033[0m")

if __name__ == "__main__":
    main()