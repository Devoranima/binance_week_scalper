from flask import Flask, request, jsonify
from telegram.ext import Application

from bot.config import CHAT_ID, CONTROL_BOT_TOKEN


app = Flask(__name__)
application = Application.builder().token(CONTROL_BOT_TOKEN).build()

@app.before_request
def check_origin():
    if request.remote_addr != "127.0.0.1":
        return jsonify({"error": "Unauthorized"}), 403

@app.route("/debug", methods=["GET"])
async def debug():
    print("getting something")
    await application.bot.send_message(
        chat_id=CHAT_ID,
        text="Getting something"
    )
    return jsonify({"status": "sent"}), 200

@app.route("/swing-updates", methods=["POST"])
async def send_new_swings():
    swings = request.get_json()
    if not swings:
        return jsonify({"error": "No data provided"}), 400
    
    await application.bot.send_message(
        chat_id=CHAT_ID, text=f"New Swings Alert:\n{len(swings)}")
    message = "Tradepair | Timeframe | Orientation\n"
    message += '\n'.join([f"{swing['tradepair']} | {swing['timeframe']} | {swing['swing_type']}" for swing in swings])
    await application.bot.send_message(
        chat_id=CHAT_ID, text=message
    )
    return jsonify({"status": "sent"}), 200


@app.route("/newSwing", methods=["POST"])
async def send_new_swing():
    """Accept new swing data from the local API and notify the admin."""
    
    data = request.get_json()
    swing = data.get("swing")

    if not swing:
        return jsonify({"error": "No swing data provided"}), 400

    # Send message to the admin
    await application.bot.send_message(
        chat_id=CHAT_ID, text=f"New Swing Alert:\n{swing}")
    return jsonify({"status": "sent"}), 200

def startBot():
    app.run(host='127.0.0.1', port=7670, debug=True, use_reloader=False)