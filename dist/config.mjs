export const baseline = {
  active_mode: "long_term_quality",
  modes: {
    long_term_quality: { player_impact: .45, low_effort: .15, unblocks_work: .4, rework_risk: -.3, relevance: .25 },
    demo_crunch: { player_impact: .4, low_effort: .3, unblocks_work: .3, rework_risk: -.15, relevance: .25 }
  },
  thresholds: { readiness_gate: 4, score_cutoff: 1 },
  capacity: { programming: 1, music: 1, art: 2, gameplay: 5 }, completed: [],
  tasks: [
    { id:"finish_art_music", signals:{player_impact:4,low_effort:2.5,unblocks_work:4,rework_risk:2.5,relevance:4.5}, readiness:4, depends_on:[], needs:{programming:1,music:1,art:2,gameplay:0} },
    { id:"get_playtesters", signals:{player_impact:4,low_effort:4,unblocks_work:2.5,rework_risk:1,relevance:5}, readiness:5, depends_on:[], needs:{programming:0,music:0,art:0,gameplay:1} },
    { id:"make_trailer", signals:{player_impact:2.5,low_effort:3,unblocks_work:1,rework_risk:5,relevance:3.5}, readiness:1, depends_on:["finish_art_music"], needs:{programming:0,music:1,art:1,gameplay:0} },
    { id:"fix_audio_bug", signals:{player_impact:3,low_effort:5,unblocks_work:1,rework_risk:1,relevance:2}, readiness:5, depends_on:[], needs:{programming:1,music:1,art:0,gameplay:0} },
    { id:"fix_menu", signals:{player_impact:4,low_effort:3,unblocks_work:2,rework_risk:1,relevance:4}, readiness:4, depends_on:[], needs:{programming:1,music:0,art:0,gameplay:0} }
  ]
};
