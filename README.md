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

예를 들어 경로가 1*file*C:\A\B\C\D\x_sound1.mp3인 경우,
For example, if the path is 1*file*C:\A\B\C\D\x_sound1.mp3
형식은 숫자*file*경로입니다. 
the format should be number*file*path. On the web
웹에서는 x_sound1이라는 이름만 표시됩니다. 
On the web, only x_sound1 will be displayed as the name.

audio_file_list에 예시도 하나 넣어놓았습니다. 
An example has been included in audio_file_list.

어떻게 쓰는지 알 것 같다면, 지우고 사용하시면 됩니다.
If you understand how to use it, feel free to delete the example and start using it.
