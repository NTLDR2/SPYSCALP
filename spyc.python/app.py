from flask import Flask

app = Flask(__name__)


@app.route('/')
def home():
    # Return the text you want to display in the browser
    x = 2 + 2

    return "Two plus two equals", x


# Run the application (only if script is executed directly)
if __name__ == '__main__':
    app.run(debug=True)     # REMINDER: Come back to this line.
    # Does the debug=True line need to stay there forever?