{ ... }:

{
  services.fail2ban.enable = true;
  services.fail2ban.maxretry = 5;
  services.fail2ban.bantime = "1h";
  services.fail2ban.bantime-increment = {
    enable = true;
    # formula = "ban.Time * math.exp(float(ban.Count+1)*banFactor)/math.exp(1*banFactor)";
    multipliers = "1 2 4 8 16 32 64";
    maxtime = "168h"; # Do not ban for more than 1 week
    overalljails = true; # Calculate the bantime based on all the violations
  };
  services.fail2ban.jails = {
    sshd.settings = {
      # Nix comes with a default SSHD jail
      enabled = true;
    };
  };
}
