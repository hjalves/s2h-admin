# s2h-admin

This is a web admin interface for shell2http, powered by Python and shell2http itself. 

I've written a blog post about this project here: 
https://halves.dev/posts/2023/02/building-an-admin-interface-for-shell2http/

## Getting Started

Clone this repo, or download the single `s2h_admin.py` source file.
If you want to run a development server, execute in a command line 
`./s2h_admin.py serve` or `python s2h_admin.py serve`.

To run it with shell2http and a systemd unit file, see below.

## Prerequisites

- Python 3.8+
- [shell2http](https://github.com/msoap/shell2http)
- systemd (user's instance)

## Installing

1. Download and install shell2http from here: https://github.com/msoap/shell2http/releases

2. Download the single `s2h_admin.py` file in a directory located in your home dir (`~`).
At this moment, it cannot be placed outside the home dir, like `/opt/`.

3. You may use the command `./s2h_admin.py unit-file` to generate a systemd `.service`
file, so you can install it on your systemd's user unit directory, typically 
located in `~/.config/systemd/user/`.

4. Reload daemon and restart systemd service, with `systemctl --user reload-daemon`
followed by `systemctl --user restart shell2http`.

## Contributing

If you want to send bug fixes or improvements, you can submit a pull request.
Also, feel free to open an issue for bug reports, questions or suggestions 
you may have.


## License

MIT
