export IB_PASSWORD=$(aws ssm get-parameter --name ib_password --with-decryption | jq -r ".Parameter.Value")
export IB_USER=$(aws ssm get-parameter --name ib_user --with-decryption | jq -r ".Parameter.Value")
export TWS_LIVE_PAPER=$(aws ssm get-parameter --name ib_mode --with-decryption | jq -r ".Parameter.Value")

