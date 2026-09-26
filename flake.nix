{
  description = "Veno's Blog (Hugo, hugo-theme-stack)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "aarch64-darwin"
        "x86_64-darwin"
        "x86_64-linux"
        "aarch64-linux"
      ];
    in {
      # `nix develop`, then `hugo server`. The theme is a git submodule:
      # `git submodule update --init` first on a fresh clone.
      #
      # Mirrors .github/workflows: nixpkgs' hugo is the extended build, and
      # dart-sass matches the CI install. Keep HUGO_VERSION there in step with
      # the hugo this flake.lock pins.
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = [ pkgs.hugo pkgs.dart-sass pkgs.git ];
          };
        });
    };
}
