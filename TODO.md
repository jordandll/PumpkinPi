Make the app configurable so that default values for the `--host` and `--port` parameters can be stored in a config file.

On Linux systems, the config file should be stored in `~/.local/etc/pumpkinpi_config.d` -- if you have a better suggestion, let me know -- with instructions on how to set the configurable parameters.  On other systems, I'll let you decide where and how to store the config values.

The values set in this file must apply to any `pumpkinpi` command with these parameters -- e.g. `server`, `client`, etc. -- so the implementing scripts should parse said file in the absense of command line arguments for the relevant parameters.

Arguments passed to `pumpkinpi` commands on the command line must take precedence over values set in the config file.