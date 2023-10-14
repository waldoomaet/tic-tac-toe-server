import logging
import json
from enum import Enum
from websocket_server import WebsocketServer

max_players = 2
client_player = {}


class Status(str, Enum):
    connected = "connected"
    started = "started"
    turn_change = "turn_change"
    game_over = "game_over"
    lose = "lose"
    draw = "draw"
    play_again = "play_again"


class Player(str, Enum):
    x = "X".upper()
    o = "O".upper()


def new_client(client, server):
    # This is a really bad practice, but 🤷‍♂️
    global client_player
    if len(server.clients) <= max_players:
        if Player.x not in client_player.values():
            client_player[client["id"]] = Player.x
        else:
            client_player[client["id"]] = Player.o
        
        server.send_message(
            client,
            json.dumps(
                {
                    "status": Status.connected,
                    "id": client["id"],
                    "player": client_player[client["id"]],
                }
            ),
        )

        print(f"Player {client_player[client['id']]} connected!")
        if len(server.clients) == max_players:
            server.send_message_to_all(
                json.dumps({"status": Status.started})
            )
            server.deny_new_connections()


def client_disconnected(client, server):
    global client_player
    del client_player[client["id"]]
    server.allow_new_connections()


def new_message(sender_client, server, message):
    data = json.loads(message)
    if data["status"] == Status.turn_change:
        for client in server.clients:
            if sender_client["id"] != client["id"]:
                server.send_message(
                    client,
                    json.dumps({"status": Status.turn_change, "board": data["board"]}),
                )
                break
    if data["status"] == Status.game_over:
        # show_winner()
        for client in server.clients:
            if sender_client["id"] != client["id"]:
                server.send_message(
                    client,
                    json.dumps({"status": Status.lose, "board": data["board"]}),
                )
                break
    if data["status"] == Status.draw:
        server.send_message_to_all(json.dumps({"status": Status.draw}))
    if data["status"] == Status.play_again:
        server.send_message_to_all(json.dumps({"status": Status.play_again}))


server = WebsocketServer(host="0.0.0.0", port=13254, loglevel=logging.INFO)
server.set_fn_new_client(new_client)
server.set_fn_message_received(new_message)
server.set_fn_client_left(client_disconnected)
server.run_forever()
