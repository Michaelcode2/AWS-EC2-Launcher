# Customer onboarding

EC2 Desktop Manager is a Windows desktop client. **AWS IAM is the
authorization boundary.** A local TOML profile only controls what the
application shows. It cannot grant Start, Stop, or Restart.

## Prerequisites

- Windows 10/11 x64
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- An IAM Identity Center user with a permission set that allows EC2 describe
  plus the actions you intend to expose (see `docs/iam-desktop-policy.json`)
- An AWS CLI SSO profile, for example:

  ```ini
  [profile customer-server]
  sso_start_url = https://example.awsapps.com/start
  sso_region = eu-central-1
  sso_account_id = 123456789012
  sso_role_name = Ec2DesktopOperator
  region = eu-central-1
  ```

## Application profile

Copy `config/example-profile.toml` to
`%LOCALAPPDATA%\Ec2DesktopManager\config\` and set:

- `expected_account_id` to the 12-digit account
- `default_region`
- `[aws] profile` to the CLI profile name
- filters (`all`, `instance_ids`, or `tags`)
- feature flags to hide Start/Stop/Restart if needed

Never store secret keys, session tokens, or Windows passwords in the TOML file.

## First sign-in

1. Install the application (Python is not required on the customer PC).
2. Start EC2 Desktop Manager.
3. Select the customer profile and choose **Sign in**.
4. Complete IAM Identity Center in the browser. Do not type an AWS console
   password into this application.
5. The main window opens only if STS `GetCallerIdentity` matches
   `expected_account_id`.

## Idle auto-stop

The desktop client does not stop idle instances. Install
`scripts/idle-stop/` on the Windows EC2 instance itself. See
`scripts/idle-stop/README.md`.
