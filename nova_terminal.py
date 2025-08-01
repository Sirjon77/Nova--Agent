
def nova_terminal():
    print("Nova Terminal Ready. Commands:")
    print("1: Reflect")
    print("2: Load New Modules")
    print("3: Run Diagnostics")
    choice = input("Choose command: ")
    if choice == "1":
        from reflection_loop import run_reflection_loop
        run_reflection_loop()
    elif choice == "2":
        from nova_module_loader import dynamic_module_loader
        dynamic_module_loader()
    elif choice == "3":
        from nova_selftest import run_nova_selftest
        run_nova_selftest()
    else:
        print("Unknown command.")
