#!/bin/bash
# Syncs the local directory with its corresponding debug pod

oc project

while true; do (
    DC=configmaster
    POD=$(oc get pod -l deploymentconfig=${DC} -o name|cut -f2 -d/)

    oc rsync --delete=true . ${POD}: \
        --exclude=.s2i

    echo "Watching for changes - press Ctrl-C to exit"

    coproc oc rsh ${POD}

    while read line
    do
        filename=$(echo "$line" | grep -vF '___')

        # Short-lived temporary files
        if [[ ! -e "$filename" ]]; then
          continue
        fi

        if [[ ! -z $filename ]]; then
          echo "Syncing $filename"
          echo "cat <<'eiLi5bie' > $filename" >&"${COPROC[1]}"
          cat "$filename"  >&"${COPROC[1]}"
          echo "eiLi5bie" >&"${COPROC[1]}"
          echo "Done"
        fi
    done < <(inotifywait -mr -e moved_to,modify --format %w%f .)
)
done
