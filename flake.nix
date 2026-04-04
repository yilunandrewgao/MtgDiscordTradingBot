{
  description = "MTG Discord Trading Bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python313;
      in
      {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "mtg-discord-trading-bot";
          version = "0.1.0";
          pyproject = true;

          src = ./.;

          build-system = [ python.pkgs.hatchling ];

          dependencies = with python.pkgs; [
            curl-cffi
            discordpy
            python-dotenv
            parsy
          ];

          nativeCheckInputs = [ python.pkgs.pytestCheckHook ];

          disabledTestPaths = [
            "tests/test_main_integration.py"
            "tests/test_moxfield_api_integration.py"
            "tests/test_trader_integration.py"
          ];

          preCheck = ''
            export DISCORD_TOKEN=dummy
          '';
        };

        checks.tests = self.outputs.packages.${system}.default;
      }
    )
    // {
      nixosModules.default =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        let
          cfg = config.services.mtg-discord-bot;
          pkg = self.packages.${pkgs.system}.default;
        in
        {
          options.services.mtg-discord-bot = {
            enable = lib.mkEnableOption "MTG Discord Trading Bot";

            tokenFile = lib.mkOption {
              type = lib.types.path;
              description = ''
                Path to a file containing the Discord bot token, in
                KEY=VALUE format: DISCORD_TOKEN=your-token-here
              '';
            };

            dataDir = lib.mkOption {
              type = lib.types.str;
              default = "/var/lib/mtg-discord-bot";
              description = ''
                Directory for bot state (users.json and logs).
                The bot process runs with this as its working directory.
              '';
            };

            user = lib.mkOption {
              type = lib.types.str;
              default = "mtg-discord-bot";
              description = "User account under which the bot runs.";
            };

            group = lib.mkOption {
              type = lib.types.str;
              default = "mtg-discord-bot";
              description = "Group under which the bot runs.";
            };
          };

          config = lib.mkIf cfg.enable {
            users.users.${cfg.user} = {
              isSystemUser = true;
              group = cfg.group;
              home = cfg.dataDir;
              createHome = true;
            };

            users.groups.${cfg.group} = { };

            systemd.services.mtg-discord-bot = {
              description = "MTG Discord Trading Bot";
              wantedBy = [ "multi-user.target" ];
              after = [ "network-online.target" ];
              wants = [ "network-online.target" ];

              serviceConfig = {
                ExecStart = "${pkg}/bin/mtg-discord-bot";
                WorkingDirectory = cfg.dataDir;
                EnvironmentFile = cfg.tokenFile;
                User = cfg.user;
                Group = cfg.group;
                Restart = "on-failure";
                RestartSec = "5s";
                NoNewPrivileges = true;
                PrivateTmp = true;
                ProtectSystem = "strict";
                ReadWritePaths = [ cfg.dataDir ];
              };
            };
          };
        };
    };
}
