# Operator -> drone mission commands
uint8 CMD_TAKEOFF=0
uint8 CMD_LAND=1
uint8 CMD_GOTO_PERSON=2
uint8 CMD_RETURN_HOME=3
uint8 CMD_ABORT=4
uint8 command
uint32 target_id          # person index for GOTO_PERSON
float64 target_x
float64 target_y
