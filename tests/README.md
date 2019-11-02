# Tests

These tests are batch files that can be run on Windows OS.
They test the 3 functions: `put`, `get`, `ls`.

## Usage

1. Run `start_server.bat` file
2. Run the desired test batch files (double click), and they will run the client (server must be active).

If an error occurs and the server crashes, the server must be run again.
If the server is giving the error: 

```
OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted
```

This means that there is a server already running, and you may need to kill the process (see main readme).
