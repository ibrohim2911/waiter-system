# waiter system

## Running the application

### With Waitress (Production-like)
To run the server, you have to install all the required dependencies. To do so, run `pip install -r requirements.txt`.

Then, you can run the application by running the command:
```bash
python run_waitress.py
```

This will start the server on `http://0.0.0.0:8000`.

## Building an Executable

I have created a `waiter_waitress.spec` file to build a standalone executable that uses the Waitress server.

To build the executable, run the following command:
```bash
pyinstaller waiter_waitress.spec
```

This will create a `dist` folder containing `RestaurantServer_Waitress.exe`.

**Note:** I was unable to read the original `waiter.spec` file, so I created a new one. You may need to adjust `waiter_waitress.spec` to include other dependencies or options from your original file.
