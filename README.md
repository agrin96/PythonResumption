# Resumption

This is a silly piece of python software that demonstrates code resumption on python. In practice this means that for very simple cases you can `KeyBoardInterrupt` some code and it will be resumed from the interrupt location.

What possessed me to do this is simple curiosity. Could I rerun/restore a running python script? The answer is yes, but with many many caveats.

Please note this is not a fully working/feature complete solution. I haven't tested it on any complex or real-world python scripts. As such a lot of the source is still underdeveloped.

## Details

The solution I came up with to do resumption is bytecode patching and gotos. We first split the source code into each frame and insert jumps from the beginning of the current frame to the line that opened the next frame (In our case the function call). We translate those jumps on the bytecode level into `JUMP` instructions and then the real magic happens. Because there may have been variable initializations between the jump start and jump destination, we find the local and global declarations between those two points and we hoist them right above the `JUMP_FORWARD` instruction. This means that even after we jump over the original location of these declarations, they should still be loaded into memory.

This approach only works for very simple cases however, as any variable mutations done in the source are not accounted for. I do believe that it is possible with a lot of pain to account even for that scenario, but that is left up to the next crazy person who reads this (or maybe me in a few months time).

# Example

You can run the example code in `src/__main__.py` to see how this works. (Optionally you can enable debug in that file to get some more information). The test script we are running is `test_source.py` which has a sleep timer of 3 seconds during which we can trigger the interrupt and have the (heretical) magic happen. The source code is manipulated on the bytecode level and reconstructed to then be re-run from the interrupt point.

After runnign the script you should see the corresponding output.

```bash
❯ python src/__main__.py
DEBUG: Running source test_source.py
Starting 'Nothing to see here''
Ready to Interrupt
^C
DEBUG: Interrupted run
DEBUG: Resuming code
Resumed
Python Heresy successfully committed: 5
May Guido Forgive me
```

## Acknowledgments

I took some inspiration from [this implementation of goto in python](https://github.com/cdjc/goto). I re-implemented some of the behavior of this library, but notably I needed a solution to allow jumping through scopes. To solve this issue I emmbed multiple goto statements, one set per scope.