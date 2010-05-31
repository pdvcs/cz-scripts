            // Lookup tables for days in month and month names
			var mtbl  = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
            var mnames = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"];
            
			// End-of-month Julian Day lookup tables for normal and leap years
            var jdtbln = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
            var jdtbll = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];
            
			var leap = false;
            var jdtbl = jdtbln;
            var yearpattern = /^\d{4,5}$/;
            var displayStyle = "std";
			var d, time;

            var timeDiff = {
                setStartTime : function () {
                    d = new Date();
                    time  = d.getTime();
                },

                getDiff : function () {
                    d = new Date();
                    return (d.getTime()-time);
                }
            };
            
            function isLeap (year) {
                return (year % 100 !== 0) && (year % 4 === 0) || (year % 400 === 0);
            }
            function julianDay (day, month) {
                return day + jdtbl[month-1];
            }

            // returns the day of week as an integer: 1=Sun, 2=Mon, ..., 7=Sat
            function dayOfWeek (day, month, year) {
                leap = isLeap(year);
                jdtbl = leap? jdtbll : jdtbln;
                var dow = (year + julianDay(day, month) + Math.floor((year-1)/4) - Math.floor((year-1)/100) + Math.floor((year-1)/400)) % 7;
                return dow === 0? 7: dow;
            }

            function renderMonth (parent, month, year) {
                var dateCells = $(parent + " td.dt");
                var cellid = dayOfWeek(1, month, year) - 1;
                var max = mtbl[month-1];
                if (max === 28 && leap) { max = 29; }

                dateCells.eq(cellid++).html(1);
                for (var ix = 2; ix <= max; ix++) {
                    dateCells.eq(cellid++).html(ix);
                }
                $(parent + " td.mo").html(mnames[month-1]);
            }
            
            function getMonthSequence (mainMonth) {
                var tmp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
                if (mainMonth === 0) { return tmp; }
                
                var monthseq = [];
                monthseq.push(mainMonth);
                if (mainMonth === 11) {
                    // n+1 isn't possible
                    monthseq.push(9);
                    monthseq.push(10);
                    tmp.splice(9, 3);
                } else {
                    monthseq.push(mainMonth-1);
                    monthseq.push(mainMonth+1);
                    tmp.splice(mainMonth-1, 3);
                }
                return monthseq.concat(tmp);
            }

            function getIdPrefix (ix) {
                if (ix < 3 && displayStyle === "alt1") {
                    return "#p2-";
                } else {
                    return "#p";
                }
            }

            function showSelective () {
                $("#helptext").hide();
                $("#aboutlink").show();
                $("div#cal").show();
                if (displayStyle === "alt1") {
                    $("#mtoprow").hide();
                    $("#mtoprow2").show();
                } else {
                    $("#mtoprow").show();
                    $("#mtoprow2").hide();
                }
            }
            
            function renderCalendar (startMonth, stopMonth, year) {
                timeDiff.setStartTime();
                displayStyle = $("#dispstyle").val();
                var d = new Date();
                var seqargs = 0;
                if (displayStyle === "alt1") {
                    seqargs = (d.getFullYear() === year? d.getMonth(): 0);
				}
                var monthHtml = $("span#m0").html();
                var monthseq = getMonthSequence(seqargs);

                $("#caltitle").text(year);
                for (var ix = startMonth-1; ix < stopMonth; ix++) {
                    var newId = getIdPrefix(ix) + ix;
                    if ($(newId).length === 1) {
                        $(newId).html(monthHtml);
                        renderMonth(newId, monthseq[ix]+1, year);
                    }
                }

                showSelective();

                // benchmarking
                var elapsed = timeDiff.getDiff();
                $("#bm").text(" | Page rendered in " + elapsed + " ms.").show();
            }
			

			function button_enable (btnid) {
                $(btnid).removeAttr("disabled");
                $(btnid).css("color", "#000");
            }
            function button_disable (btnid) {
                $(btnid).attr("disabled", "true");
                $(btnid).css("color", "#aaa");
            }

            $(document).ready(function () {

				function initButtons () {
					button_disable("#print");
					$("#show").click(function (evt) {
						var selectedYear = parseInt($("#yearsel").val(), 10);
						evt.preventDefault();
						renderCalendar(1, 12, selectedYear);
						document.title = selectedYear + " Calendar";
						button_enable("#print");
					});
					$("#print").click(function (evt) {
						window.print();
					});
					$("#aboutlink").click(function (evt) {
						evt.preventDefault();
						if ($("#aboutlink").html() === "| <a href=\"#\">Show Page Info</a>") {
							$("#helptext").show();
							$("#aboutlink").html("| <a href=\"#\">Hide Page Info</a>");
						} else {
							$("#helptext").hide();
							$("#aboutlink").html("| <a href=\"#\">Show Page Info</a>");
						}
					});
				}
				
                initButtons();
                
                var inputbox = $("#yearsel");
                inputbox.val(new Date().getFullYear());
                inputbox.focus();
                
                inputbox.keyup(function (e) {
                    if (!yearpattern.test(inputbox.val()) || parseInt(inputbox.val(), 10) < 1583 || parseInt(inputbox.val(), 10) > 25000) {
                        inputbox.attr("style", "background: #ffdae7;");
                        button_disable("#show");
                    } else {
                        inputbox.attr("style", "background: white;");
                        button_enable("#show");
                        if (e.keyCode === 13) {
                            $("#show").click();
                        }
                    }
                });
            });
