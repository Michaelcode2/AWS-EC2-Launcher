# ec2-inventory Specification

## Purpose
Discovers EC2 instances the authenticated principal can see, applies local presentation filters, and keeps the displayed inventory current.
## Requirements
### Requirement: Regional discovery with pagination
The application SHALL list instances in the selected region using paginated DescribeInstances so multiple reservations and API pages are included.

#### Scenario: Multiple API pages
- **WHEN** the region contains more instances than fit on one DescribeInstances page
- **THEN** the inventory includes instances from every page

### Requirement: Instance display fields
Each listed instance SHALL include instance ID, name from the Name tag with instance ID fallback, state, instance type, availability zone, private IP, public IP, Elastic IP when present, tags, and last refresh time.

#### Scenario: Name tag present
- **WHEN** an instance has a Name tag
- **THEN** the table Name column shows that tag value

#### Scenario: Name tag missing
- **WHEN** an instance has no Name tag
- **THEN** the table Name column falls back to the instance ID

### Requirement: Filter modes
The application SHALL support filter modes `all`, `instance_ids`, and `tags` from the selected profile. Filters MUST only reduce what is shown; they MUST NOT grant access beyond IAM.

#### Scenario: All visible instances
- **WHEN** the profile filter mode is `all`
- **THEN** every instance returned by DescribeInstances in the region is listed

#### Scenario: Instance ID filter
- **WHEN** the profile filter mode is `instance_ids`
- **THEN** only instances whose IDs are in the configured list are listed

#### Scenario: Tag filter
- **WHEN** the profile filter mode is `tags`
- **THEN** only instances that have all configured tag key/value pairs are listed

### Requirement: Filter is not authorization
If a user changes the local filter to include an instance IAM does not authorize for actions, the application SHALL still list it only if DescribeInstances returns it, and subsequent actions SHALL still fail or succeed based on AWS.

#### Scenario: Filter expanded locally
- **WHEN** the user edits the local filter to include another instance ID that DescribeInstances returns
- **THEN** the instance may appear in the table, but Start, Stop, and Restart still succeed or fail according to AWS IAM

### Requirement: Manual and timed refresh
The application SHALL refresh inventory on demand and on a timed interval from configuration, defaulting to 15 seconds.

#### Scenario: Manual refresh
- **WHEN** the user chooses Refresh
- **THEN** inventory and displayed states are updated from AWS

#### Scenario: Timed refresh
- **WHEN** the refresh interval elapses while the main window is open
- **THEN** inventory is refreshed without requiring another login

