# ========================================================================== #
#                                                                            #
#    KVMD - The main Pi-KVM daemon.                                          #
#                                                                            #
#    Copyright (C) 2018  Maxim Devaev <mdevaev@gmail.com>                    #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation, either version 3 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                            #
# ========================================================================== #


import os
import secrets
import multiprocessing
import multiprocessing.queues
import time

import setproctitle

from kvmd.apps.cleanup import main


# =====
def test_ok(tmpdir) -> None:  # type: ignore
    queue: multiprocessing.queues.Queue = multiprocessing.Queue()

    ustreamer_tmp_path = os.path.abspath(str(tmpdir.join("ustr-" + secrets.token_hex(3))))
    os.symlink("/usr/bin/ustreamer", ustreamer_tmp_path)

    ustreamer_sock_path = os.path.abspath(str(tmpdir.join("ustreamer-fake.sock")))
    open(ustreamer_sock_path, "w").close()
    kvmd_sock_path = os.path.abspath(str(tmpdir.join("kvmd-fake.sock")))
    open(kvmd_sock_path, "w").close()

    def ustreamer_fake() -> None:
        setproctitle.setproctitle(os.path.basename(ustreamer_tmp_path))
        queue.put(True)
        while True:
            time.sleep(1)

    proc = multiprocessing.Process(target=ustreamer_fake, daemon=True)
    proc.start()
    assert queue.get(timeout=5)

    assert proc.is_alive()
    main([
        "kvmd-cleanup",
        "--set-options",
        "kvmd/server/port=0",
        "kvmd/server/unix=" + kvmd_sock_path,
        "kvmd/streamer/port=0",
        "kvmd/streamer/unix=" + ustreamer_sock_path,
        "kvmd/streamer/cmd=" + ustreamer_tmp_path,
    ])

    assert not os.path.exists(ustreamer_sock_path)
    assert not os.path.exists(kvmd_sock_path)

    assert not proc.is_alive()
    proc.join()