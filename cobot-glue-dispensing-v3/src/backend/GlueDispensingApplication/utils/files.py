def write_to_debug_file(file_name,message):
    try:

        with open(file_name, "a") as _f:
            _f.write(message)
    except Exception as _e:
        print(f"Error writing content {message} to file {file_name}: {_e}")