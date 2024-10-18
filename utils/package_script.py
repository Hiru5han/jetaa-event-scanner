import os
import subprocess


def run_shell_command(command):
    """Run a shell command and print the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {command}: {result.stderr}")
    else:
        print(f"Executed {command} successfully.")


def main():
    # Step 1: Generate requirements.txt
    print("Generating requirements.txt...")
    run_shell_command("pip freeze > requirements.txt")

    # Step 2: Install dependencies into a specific target directory
    print("Installing dependencies to ./package directory...")
    run_shell_command("pip install -r requirements.txt --target ./package")

    # Step 3: Zip everything except certain directories
    print("Creating the initial function.zip, excluding unnecessary directories...")
    run_shell_command("zip -r function.zip . -x '__pycache__/*' 'venv/*' '.git/*'")

    # Step 4: Change directory to 'package'
    print("Changing directory to 'package'...")
    os.chdir("package")

    # Step 5: Add the contents of 'package' to the existing function.zip
    print("Adding contents of 'package' to function.zip...")
    run_shell_command("zip -r ../function.zip .")

    # Step 6: Go back to the previous directory
    print("Going back to the original directory...")
    os.chdir("..")

    # Step 7: Add Python files and logos to the function.zip
    print("Adding Python files and logos to function.zip...")
    run_shell_command("zip -g function.zip *.py event_source_logos/*")

    print("Packaging completed successfully.")


if __name__ == "__main__":
    main()
