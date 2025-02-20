from agent.tools.terminals_linux import open_terminal, command_terminal, get_terminal_output, close_terminal, rename, list_all, help
import time
def test_terminals():
    print(open_terminal("R_script"))
    print(command_terminal(name="R_script", command="Rscript ~/202B/gradient-descent-regression-bls-HW1.R"))
    # print(get_output(name="R_script"))
    # print(close(name="test"))
    # print(rename(name="test", new_name="test2"))
    # print(list())
    # print(help())

if __name__ == "__main__":
    test_terminals()