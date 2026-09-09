# Chess Puzzles

## Running the pipeline as a cron job

The main pipeline wrapper is at `pipeline/pipeline.sh`. It downloads yesterday's games, processes them with Stockfish, and appends any found puzzle positions to `data/puzzles.txt`.

By default all data goes into `data/` under the project root. You can override this by setting `DATA_DIR`:

```bash
DATA_DIR=/some/other/dir ./pipeline/pipeline.sh
```

### Setting up cron

1. Make sure the scripts are executable:

```bash
chmod +x pipeline/pipeline.sh
chmod +x pipeline/retrieve_games.sh
chmod +x pipeline/process_game.sh
```

2. Open your crontab:

```bash
crontab -e
```

3. Add an entry. For example, to run every day at 06:00:

```cron
0 6 * * * /home/nisha/workspace/chess_puzzles/pipeline/pipeline.sh >> /home/nisha/workspace/chess_puzzles/data/cron.log 2>&1
```

Adjust the schedule and log path as needed.

4. Run the TUI against the generated `puzzles.txt`:

```bash
python3 chess_puzzles.py data/puzzles.txt
```
