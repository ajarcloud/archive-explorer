#!/bin/bash
# Launch a terminal window with a tmux session for archive-explorer development.
#
# Layout (single window):
#   +------------------+------------------+
#   |                  |   frontend dev   |
#   |   shell          +------------------+
#   |                  |   backend dev    |
#   +------------------+------------------+

SESSION="archive-explorer"
BACKEND="$(dirname "$0")/backend"
FRONTEND="$(dirname "$0")/frontend"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  osascript -e "tell app \"Terminal\" to do script \"tmux attach -t $SESSION\""
  exit 0
fi

tmux new-session -d -s "$SESSION" -c "$BACKEND"
tmux send-keys 'source venv/bin/activate && clear' Enter

# Right column — split vertically
tmux split-window -h -c "$FRONTEND"
tmux send-keys 'npm run dev' Enter

# Bottom-right — backend dev server
tmux split-window -v -c "$BACKEND"
tmux send-keys 'source venv/bin/activate && uvicorn app.main:app --reload --port 8000' Enter

# Give the left (shell) pane more room
tmux resize-pane -t 0 -x 80

osascript -e "tell app \"Terminal\" to do script \"tmux attach -t $SESSION\""
