from tools.database import DataBaseController, \
                           CommandProcessor, \
                           MyException

def main():
    controller = DataBaseController()
    processor = CommandProcessor(controller, print)

    while (command := input('> ')) != 'exit':
        try:
            processor.process(command)
        except MyException as ex:
            print(ex)

if __name__ == '__main__':
    main()

