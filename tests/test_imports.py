def test_loop_engineering_package_exposes_version():
    import loop_engineering

    assert loop_engineering.__version__ == "0.1.0"
