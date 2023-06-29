#!/bin/bash
usage() {
  echo "STM32CubeIDE build utility"
  echo "Usage:"
  echo "- [-v] to activate verbose mode"
  echo "- [-s] supress build process logs, show only build result"
  echo "- [-w workspace_path] to specify workspace path"
  echo "- [-c cube_ide_path] to specify STM32CubeIDE path"
  echo "- [-p Project name] to specify project name"
  echo "Example: $0 -v -w $WS_PATH -c $CUBE_IDE_PATH -p $PROJECT_NAME";
  echo "Another example: $0 -v -w $WS_PATH -c /opt/stm32cubeide/stm32cubeide -p $PROJECT_NAME";
  exit 1;
}

cubeide_build() {
  if [ $SUPRES_BUILD_LOG -eq 1 ]; then
    $CUBE_IDE_PATH $BUILD_ARGS -import $PROJECT_PATH -build $PROJECT_NAME -data $WS_PATH | grep "Opening\|Build of configuration \|Build Finished"
  else
    $CUBE_IDE_PATH $BUILD_ARGS -import $PROJECT_PATH -build $PROJECT_NAME -data $WS_PATH
  fi
}

# 1. Init params by default
CUBE_IDE_PATH=/opt/st/stm32cubeide_1.5.1/stm32cubeide
WS_PATH=~/STM32CubeIDE/workspace_1.5.1
VERBOSE=0
SUPRES_BUILD_LOG=0
PROJECT_NAME=charger
PROJECT_PATH=.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# 2. Parse arguments and use custom params
while getopts "w:c:p:vsh" opt
do
case $opt in
  w) WS_PATH=${OPTARG};;
  c) CUBE_IDE_PATH=${OPTARG};;
  p) PROJECT_NAME=${OPTARG};;
  v) VERBOSE=1;;
  s) SUPRES_BUILD_LOG=1;;
  h) usage ;;
  *) usage ;;
esac
done

# 3. Verbose
if [ $VERBOSE -eq 1 ]; then
  echo "Workspace path: ${WS_PATH}"
  echo "CubeIde path: ${CUBE_IDE_PATH}"
  echo "Project name: ${PROJECT_NAME}"
  echo ""
fi

# 4. Build
cd $SCRIPT_DIR/..
BUILD_ARGS="--launcher.suppressErrors -nosplash -application org.eclipse.cdt.managedbuilder.core.headlessbuild"
cubeide_build
