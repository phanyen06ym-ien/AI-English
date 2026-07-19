import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import AIEnglish

Item {
    id: root
    property bool running: false
    property string status: "Webcam chưa bật"

    Connections {
        target: webcamController
        function onFrameReady(img) {
            videoItem.setImage(img)
            root.running = true
        }
        function onStatusChanged(msg) {
            root.status = msg
            root.running = false
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
                text: root.status
                color: "#a4988a"
                font.pixelSize: 15
                visible: !root.running
            }
        }

        RowLayout {
            spacing: 12
            AppButton {
                text: "Bật webcam"
                onClicked: webcamController.start()
            }
            AppButton {
                text: "Tắt webcam"
                onClicked: webcamController.stop()
            }
        }
    }
}
