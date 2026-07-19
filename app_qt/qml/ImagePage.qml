import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import AIEnglish

Item {
    id: root
    property var results: []
    property bool hasImage: false
    property string placeholderText: "Chưa chọn ảnh"

    Connections {
        target: imageController
        function onImageChanged(img) {
            videoItem.setImage(img)
            root.hasImage = true
        }
        function onResultsChanged(list) {
            root.results = list
        }
        function onStatusChanged(msg) {
            root.hasImage = false
            root.placeholderText = msg
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 400
            radius: 14
            color: "#ffffff"
            border.color: "#f1e3d3"
            border.width: 1
            clip: true

            VideoItem {
                id: videoItem
                anchors.fill: parent
            }

            Text {
                anchors.centerIn: parent
                text: root.placeholderText
                color: "#a4988a"
                font.pixelSize: 15
                visible: !root.hasImage && !imageController.busy
            }

            LoadingSpinner {
                anchors.centerIn: parent
                running: imageController.busy
                visible: imageController.busy
            }
        }

        AppButton {
            text: "Chọn ảnh..."
            enabled: !imageController.busy
            onClicked: imageController.chooseImage()
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                model: root.results
                spacing: 6

                populate: Transition {
                    SequentialAnimation {
                        PauseAnimation { duration: Math.min(ViewTransition.index, 12) * 18 }
                        ParallelAnimation {
                            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 220; easing.type: Easing.OutCubic }
                            NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 220; easing.type: Easing.OutCubic }
                        }
                    }
                }

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 46
                    radius: 10
                    color: "#ffffff"
                    border.color: "#f1e3d3"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10

                        Text {
                            text: modelData.text
                            color: "#3f3628"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        AppButton {
                            text: "🔊"
                            small: true
                            onClicked: imageController.speak(modelData.english)
                        }
                    }
                }

                Text {
                    anchors.centerIn: parent
                    visible: root.results.length === 0
                    text: "Không phát hiện vật thể nào."
                    color: "#a4988a"
                }
            }
        }
    }
}
