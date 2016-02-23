import chellow

application = chellow.app
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    import argparse

    parser = argparse.ArgumentParser(description='Chellow')
    parser.add_argument('-p', '--port', default=80, type=int)
    args = parser.parse_args()

    httpd = make_server('', args.port, application)
    print("Serving HTTP on port " + str(args.port) + "...")

    # Respond to requests until process is killed
    httpd.serve_forever()
