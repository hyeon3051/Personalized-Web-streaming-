# Personalized-Web-streaming-
Personalized Web streaming(개인화된 웹 스트리밍)


project_root/
│

├── templates/
│   └── index.html

│

├── app(comment_eng, kr).py   # Python source file with English and Korean comments

├── audio_file_list           # Text file storing audio paths

├── README(eng).md            # README file in English

├── README(kr).md             # README file in Korean



It has a structure like this.

이런 구조를 하고 있습니다.

need the flask library.

flask 라이브러리가 필요합니다.

pip install flask

python app.py

pip install flask를 한 후

python app.py를 하면 실행됩니다.

audio_file_list <-- 이 파일에 오디오의 경로를 넣어야 하는데, 

You need to add audio paths to the audio_file_list.

`1*file*C:\A\B\C\D\x_sound1.mp3`
형식은 `숫자*file*경로` 입니다. 

the format should be `number*file*path`. On the web

웹에서는 x_sound1이라는 이름만 표시됩니다. 

On the web, only x_sound1 will be displayed as the name.

audio_file_list에 예시도 하나 넣어놓았습니다. 

An example has been included in audio_file_list.

어떻게 쓰는지 알 것 같다면, 지우고 사용하시면 됩니다.

If you understand how to use it, feel free to delete the example and start using it.

activity_main.xml, AndroidManifest.xml, MainActivity.java 파일은 오디오 bypass의 예제를 보여줍니다. 원한다면 jflac 라이브러리를 안드로이드 스튜디오 프로젝트에 포함시켜 앱 형태로 이용할 수 있습니다.

The activity_main.xml, AndroidManifest.xml, and MainActivity.java files show examples of audio bypass. If you wish, you can include the jflac library in your Android Studio project and use it as an app.

모든 플랫폼에서 사용하기를 바라기 때문에 ffmpeg은 첨부하지 않았습니다. 따라서 ffmpeg를 아래의 링크에서 설치 후 사용해주시기를 바랍니다.
https://ffmpeg.org/
여기서 다운로드 가능합니다.
윈도우 기준으로 기본 설치경로로 다운로드를 받았다면, 
내 PC -> 오른쪽 마우스 클릭 -> 속성 -> 고급 시스템 설정 -> 고급 -> 환경 변수 -> 사용자 변수에서 path -> 편집 -> 새로 만들기 -> C:\ffmpeg\bin 입력 -> 확인 이 순서로 진행됩니다.
요청이 많다면 조만간 윈도우 전용 브랜치를 하나 만들어 ffmpeg.exe를 추가한 브랜치를 하나 만들도록 하겠습니다.

reader.py 를 실행하면 해당 디렉토리가 생성되고, 그 디렉토리에 음원파일을 넣은 후 다시 reader.py를 실행하면 쉽게 오디오 파일 리스트를 추가할 수 있습니다.
