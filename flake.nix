{
  description = "MangoMod - GTK4/Libadwaita configuration editor for Mango Wayland compositor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];

      forEach = f:
        builtins.listToAttrs (builtins.map (system: {
          name = system;
          value = f system;
        }) systems);

      pkgsFor = system: import nixpkgs {
        inherit system;
        config = { allowUnfree = true; };
      };

      pythonWithDepsFor = pkgs: pkgs.python312.withPackages (ps: with ps; [
        pygobject3
        pycairo
        hatchling
        build
      ]);

      mangomodFor = system:
        let
          pkgs = pkgsFor system;
          pythonWithDeps = pythonWithDepsFor pkgs;
        in pkgs.python312Packages.buildPythonApplication {
          pname = "mangomod";
          version = "1.0.0";
          src = self;
          format = "pyproject";
          nativeBuildInputs = with pkgs; [
            gobject-introspection
            adwaita-icon-theme
            wrapGAppsHook3
            python312Packages.hatchling
          ];
          buildInputs = with pkgs; [ gtk4 libadwaita ];
          propagatedBuildInputs = with pkgs.python312Packages; [
            pygobject3
            pycairo
          ];
          postInstall = ''
            install -Dm644 ${self}/data/mangomod.svg $out/share/icons/hicolor/scalable/apps/io.github.mangomod.svg
            install -Dm644 /dev/stdin $out/share/applications/io.github.mangomod.desktop <<'EOF'
[Desktop Entry]
Name=MangoMod
Comment=Configuration editor for the Mango Wayland compositor
Exec=mangomod
Icon=io.github.mangomod
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;GTK;
Keywords=mango;wayland;compositor;settings;config;tiling;
StartupNotify=true
EOF
            wrapProgram $out/bin/mangomod \
              --prefix GI_TYPELIB_PATH : "${pkgs.gobject-introspection}/lib/girepository-1.0" \
              --prefix XDG_DATA_DIRS : "${pkgs.adwaita-icon-theme}/share" \
              --set GSK_RENDERER "ngl"
          '';
        };

      devShellFor = system:
        let
          pkgs = pkgsFor system;
          pythonWithDeps = pythonWithDepsFor pkgs;
        in pkgs.mkShell {
          name = "mangomod-dev";
          buildInputs = with pkgs; [
            pythonWithDeps
            gobject-introspection
            gtk4
            libadwaita
            adwaita-icon-theme
            pkg-config
            glib
          ];
          shellHook = ''
            export GI_TYPELIB_PATH="${pkgs.gobject-introspection}/lib/girepository-1.0''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
            export XDG_DATA_DIRS="${pkgs.adwaita-icon-theme}/share''${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
            export GSK_RENDERER="ngl"
            echo "MangoMod dev shell ready. Run: python -m mangomod"
          '';
        };

      checksFor = system:
        let
          pkgs = pkgsFor system;
          pythonWithDeps = pythonWithDepsFor pkgs;
        in {
          unit-tests = pkgs.stdenvNoCC.mkDerivation {
            name = "mangomod-unit-tests";
            src = self;
            nativeBuildInputs = with pkgs; [
              pythonWithDeps
              gobject-introspection
              gtk4
              libadwaita
              adwaita-icon-theme
              wrapGAppsHook3
            ];
            buildPhase = ''
              export GI_TYPELIB_PATH="${pkgs.gobject-introspection}/lib/girepository-1.0''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
              export XDG_DATA_DIRS="${pkgs.adwaita-icon-theme}/share''${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
              export GSK_RENDERER="ngl"
              PYTHONPATH=. python -m unittest discover -s tests -p 'test_*.py'
            '';
            installPhase = "touch $out";
          };
        };
    in {
      packages = forEach (system: { default = mangomodFor system; });
      devShells = forEach (system: { default = devShellFor system; });
      apps = forEach (system: let m = mangomodFor system; in { default = { type = "app"; program = "${m}/bin/mangomod"; }; });
      checks = forEach (system: checksFor system);
    };
}
