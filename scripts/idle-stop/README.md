# Idle auto-stop (on the EC2 instance)

This package is **not** installed by the desktop client and does **not** depend
on the desktop application being open.

Install it on each managed Windows EC2 instance:

1. Attach an instance profile whose policy allows `ec2:StopInstances` only on
   that instance (see `instance-profile-policy.json`).
2. Install AWS CLI v2 on the instance so it can use the instance profile.
3. From an elevated PowerShell session:

   ```powershell
   .\Install-IdleStopTask.ps1
   ```

The Scheduled Task runs `Idle-Check.ps1` every 10 minutes. After 60 minutes
with no Active RDP or console sessions, it stops **this** instance. If session
status or AWS cannot be determined, the instance is left running.

Do not put IAM access keys in these scripts.
