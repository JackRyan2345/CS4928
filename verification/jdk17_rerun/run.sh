#!/bin/bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
cd "$(dirname "$0")"   # expects ./base (clean clone @ befc7786) and ./respA (same + git apply event_b/response_A.diff)
{ echo "# run: $(date -u +%FT%TZ)  commit: $(git -C base rev-parse HEAD)"; mvn -v; java -version 2>&1; } > env.out
(cd base && mvn test) > m4_baseline_jdk17.out 2>&1
(cd respA && mvn test) > event_b_responseA_jdk17.out 2>&1
echo done > finished
