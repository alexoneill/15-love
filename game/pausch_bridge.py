from bridge import Bridge
import core

class PauschBridge(Bridge):
    def init(self):
        self.rig = core.init(upload = True, run = False, wipe = True, fire = True)

    def paint(self):
        for light in self.lights():
            # TODO: Support setting top and bottom separately (have the data,
            # just don't want to figure out the query rn)
            query = "$sequence=%d" % light.sequence
            core.query(self.rig, query).setRGBRaw(*light.color)

        self.rig.updateOnce()
