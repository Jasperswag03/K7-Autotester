import subprocess
import time
import argparse

test_count = 1

def run_k6(target_vus, duration, rampup_time, test_script, args):
    print(f"Running K6 with {target_vus} VUs for {duration}s (ramp-up: {rampup_time}s)...")
    cmd = [
        "k6", "run",
        "-e", f"VUS={target_vus}",
        "-e", f"RAMPUP={rampup_time}s",
        "-e", f"DURATION={duration}s",
        
        test_script
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate() 
    if (args.verbose):  # k6 logging if -v
        print(stdout)
        if stderr:
         print(f"Error: {stderr}")
    
    process.wait()
    return process.returncode == 0

def find_max_vus_increasing(initial_vus, increment, validation_runs, delay_between_tests, duration, rampup_time, test_script, args):
    current_vus = initial_vus
    while True:
        global test_count
        print(f"Test #{test_count}")
        test_count += 1
        passed = run_k6(current_vus, duration, rampup_time, test_script, args)
        if passed:
            print(f"Test passed for {current_vus} VUs.")
            current_vus += increment
            print(f"Waiting {delay_between_tests} seconds before the next test...\n")
            time.sleep(delay_between_tests)
        else:
            print(f"Test failed for {current_vus} VUs.")
            reduced_vus = current_vus - (increment // 2)
            print(f"Reducing VUs to {reduced_vus}. Now validating...\n")
            return find_max_vus_decreasing(reduced_vus, increment, validation_runs, delay_between_tests, duration, rampup_time, test_script, args)
            
           
            
def find_max_vus_decreasing(reduced_vus, increment, validation_runs, delay_between_tests, duration, rampup_time, test_script, args):
     while True:
                if (reduced_vus <= 0):
                    print("The VU count has reached zero. The testing process failed. Exiting...")
                    return 0
                if validate_max_vus(reduced_vus, validation_runs, delay_between_tests, duration, rampup_time, test_script, args):
                    return reduced_vus
                else:
                    print(f"Validation failed for {reduced_vus} VUs.")
                    reduced_vus -= (increment // 2)
                    print(f"Reducing VUs further to {reduced_vus} and validating again...\n")


def validate_max_vus(max_vus, validation_runs, delay_between_tests, duration, rampup_time, test_script, args):
    print(f"\033[93m\nValidating maximum VU count: {max_vus}")
    print("---------------------------\n\033[0m")
    
    for i in range(validation_runs):
        global test_count
        print(f"Test #{test_count}")
        test_count += 1
        print(f"Validation run {i+1}/{validation_runs}")
        passed = run_k6(max_vus, duration, rampup_time, test_script, args)
        if not passed:
            print(f"Validation run {i+1} failed.")
            return False
        if i + 1 < validation_runs:
             print(f"Waiting {delay_between_tests} seconds before the next validation test...\n")
        time.sleep(delay_between_tests)
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


def banner():
    print("\033[H\033[J", end="")
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RESET = "\033[0m"
    print("Automated K6 VU testing")
    print(F""" 
   {GREEN} $$\\       $$$$$$$$\\          {ORANGE} /^\\_
   {GREEN} $$ |      \\____$$  |      o_/{ORANGE}^   \\
   {GREEN} $$ |  $$\\     $$  /       /_{ORANGE}^     `_
   {GREEN} $$ | $$  |   $$  /        \\{ORANGE}/^       \\
   {GREEN} $$$$$$  /   $$  /        {ORANGE} / ^        `\\
   {GREEN} $$  _$$<   $$  /       {ORANGE} /`            `\\
   {GREEN} \\__|  \\__|\\__/       {ORANGE}  /________________|    
   
------------------------------------------------------------------------------------{RESET}""" )


if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser(description="Automated K6 VU testing.")
    parser.add_argument("-vu", "--initial_vus", type=lambda x: validate_positive_int(x, "Initial VUs"), help="Initial number of virtual users. Use a lower initial value when the tests fail immediatly.")
    parser.add_argument("-i", "--increment", type=lambda x: validate_positive_int(x, "Increment"), help="Increment for VUs. Lower values increase the accuracy of the test. however, it will take longer to find the maximum stable VU count. Recommended: 100.")
    parser.add_argument("-vr", "--validation_runs", type=lambda x: validate_positive_int(x, "Validation runs"), help="Number of validation runs (default: 4).")
    parser.add_argument("-d", "--delay_between_tests", type=lambda x: validate_positive_int(x, "Delay between tests"), help="Delay between tests in seconds (default: 10).")
    parser.add_argument("-t", "--duration", type=lambda x: validate_positive_int(x, "Duration"), help="K6 test duration in seconds (default: 60).")
    parser.add_argument("-rt", "--rampup_time", type=lambda x: validate_positive_int(x, "Rampup time"), help="Ramp-up time in seconds (default: 15).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output. Shows K6 logs.")
    parser.add_argument("--k6_script", type=str, help="Path to the K6 test script. Please refer to the template test-script.js")

    args = parser.parse_args()
    
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
                validation_runs = validate_positive_int(input("Enter the number of validation runs (recommended: 4): "), "Validation runs")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        while True:
            try:
                delay_between_tests = validate_positive_int(input("Enter the delay between tests (in seconds): "), "Delay between tests")
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
                rampup_time = validate_positive_int(input("Enter the ramp up time (in seconds): "), "Ramp up time")
                break
            except argparse.ArgumentTypeError as e:
                print(e)
        print("\033[93m------------------------------------------------------------------------------------\n\033[0m")
    else:
        validation_runs = args.validation_runs or 4
        delay_between_tests = args.delay_between_tests or 10
        duration = args.duration or 60
        rampup_time = args.rampup_time or 15

    print("\n\033[93mFinding the breakpoint.")
    print("---------------------------\n\033[0m")

    max_vus = find_max_vus_increasing(
        initial_vus,
        increment,
        validation_runs,
        delay_between_tests,
        duration,
        rampup_time,
        test_script,
        args
    )

    if max_vus > 0:
        print(f"\n\033[93m----------------------------------------------------------\nSuccessfully validated {max_vus} as the maximum stable VU count.\n----------------------------------------------------------\033[0m")
